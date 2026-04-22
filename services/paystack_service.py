import os
import time
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

PAYSTACK_SECRET  = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_BASE    = "https://api.paystack.co"

HEADERS = {
    "Authorization": f"Bearer {PAYSTACK_SECRET}",
    "Content-Type":  "application/json",
}


class PaystackService:
    """Handles all Paystack API calls — initialize, verify, charge."""

    # ── Generate a unique transaction reference ────────────────────────────
    def _new_reference(self) -> str:
        return f"SWIFTPOS-{uuid.uuid4().hex[:12].upper()}"

    # ══════════════════════════════════════════════════════════════════════
    #  MOBILE MONEY
    # ══════════════════════════════════════════════════════════════════════
    def charge_momo(
        self,
        amount_ghs: float,
        phone:      str,
        provider:   str,          # "mtn", "vodafone", "atl"
        email:      str = "customer@swiftpos.com",
    ) -> tuple[bool, str, str]:
        """
        Initiate a mobile money charge.
        Returns (success, message, reference).
        Paystack amount is in pesewas (GHS × 100).
        """
        if not PAYSTACK_SECRET:
            return False, "Paystack secret key not configured.", ""

        reference = self._new_reference()
        payload   = {
            "amount":    int(amount_ghs * 100),
            "email":     email,
            "currency":  "GHS",
            "mobile_money": {
                "phone":    phone,
                "provider": provider,
            },
            "reference": reference,
        }

        try:
            resp = requests.post(
                f"{PAYSTACK_BASE}/charge",
                json=payload,
                headers=HEADERS,
                timeout=15,
            )
            data = resp.json()

            if data.get("status") and data["data"].get("status") in (
                "send_otp", "pay_offline", "pending", "success"
            ):
                return True, data["data"].get(
                    "display_text",
                    "Prompt sent to customer's phone."
                ), reference

            msg = data.get("message") or data.get("data", {}).get(
                "message", "MoMo charge failed."
            )
            return False, msg, ""

        except requests.exceptions.ConnectionError:
            return False, "No internet connection.", ""
        except requests.exceptions.Timeout:
            return False, "Request timed out. Try again.", ""
        except Exception as e:
            return False, str(e), ""

    def submit_otp(
        self, otp: str, reference: str
    ) -> tuple[bool, str]:
        """Submit OTP for Vodafone Cash (requires OTP entry)."""
        try:
            resp = requests.post(
                f"{PAYSTACK_BASE}/charge/submit_otp",
                json={"otp": otp, "reference": reference},
                headers=HEADERS,
                timeout=15,
            )
            data = resp.json()
            if data.get("status"):
                return True, "OTP submitted."
            return False, data.get("message", "OTP failed.")
        except Exception as e:
            return False, str(e)

    # ══════════════════════════════════════════════════════════════════════
    #  CARD — payment link in browser
    # ══════════════════════════════════════════════════════════════════════
    def initialize_card_payment(
        self,
        amount_ghs: float,
        email:      str = "customer@swiftpos.com",
    ) -> tuple[bool, str, str]:
        """
        Initialize a card transaction.
        Returns (success, authorization_url, reference).
        """
        if not PAYSTACK_SECRET:
            return False, "Paystack secret key not configured.", ""

        reference = self._new_reference()
        payload   = {
            "amount":    int(amount_ghs * 100),
            "email":     email,
            "currency":  "GHS",
            "reference": reference,
            "channels":  ["card"],
        }

        try:
            resp = requests.post(
                f"{PAYSTACK_BASE}/transaction/initialize",
                json=payload,
                headers=HEADERS,
                timeout=15,
            )
            data = resp.json()

            if data.get("status"):
                url = data["data"]["authorization_url"]
                return True, url, reference

            return False, data.get("message", "Failed to initialize."), ""

        except requests.exceptions.ConnectionError:
            return False, "No internet connection.", ""
        except requests.exceptions.Timeout:
            return False, "Request timed out.", ""
        except Exception as e:
            return False, str(e), ""

    # ══════════════════════════════════════════════════════════════════════
    #  VERIFY (polls until success, failure or timeout)
    # ══════════════════════════════════════════════════════════════════════
    def verify_transaction(
        self, reference: str
    ) -> tuple[bool, str]:
        """
        Check the status of a transaction.
        Returns (success, status_string).
        status_string values: 'success' | 'failed' | 'pending' | 'abandoned'
        """
        try:
            resp = requests.get(
                f"{PAYSTACK_BASE}/transaction/verify/{reference}",
                headers=HEADERS,
                timeout=15,
            )
            data = resp.json()

            if data.get("status"):
                tx_status = data["data"]["status"]
                return True, tx_status

            return False, data.get("message", "Verification failed.")

        except requests.exceptions.ConnectionError:
            return False, "No internet connection."
        except Exception as e:
            return False, str(e)

    def poll_until_success(
        self,
        reference:    str,
        max_attempts: int = 24,     # 24 × 5s = 2 minutes
        interval_s:   int = 5,
        on_attempt:   callable = None,
    ) -> tuple[bool, str]:
        """
        Poll verify_transaction every interval_s seconds.
        Calls on_attempt(attempt, max_attempts) on each poll so
        the UI can update a progress label.
        Returns (success, final_status).
        """
        for attempt in range(1, max_attempts + 1):
            if on_attempt:
                on_attempt(attempt, max_attempts)

            ok, status = self.verify_transaction(reference)

            if not ok:
                # Network error — keep trying
                time.sleep(interval_s)
                continue

            if status == "success":
                return True, "success"
            if status in ("failed", "abandoned", "reversed"):
                return False, status

            # still pending — wait and retry
            time.sleep(interval_s)

        return False, "timeout"