import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker with India locale ('en_IN') for authentic Indian names, addresses, and companies
fake_in = Faker("en_IN")


class DynamicDataGenerator:
    """
    Generator for realistic, authentic Indian test data used across UI and API automation.
    Produces real-world, non-robotic business follow-up notes, Indian contact details,
    lead details, dates, times, and channel selections.
    """

    REALISTIC_FOLLOWUP_NOTES = [
        "Client requested updated quotation and implementation roadmap.",
        "Discussion scheduled regarding project deliverables and milestone approval.",
        "Follow up call to review the revised technical proposal and pricing details.",
        "Client requested product demonstration for the senior management team.",
        "Connect with client regarding agreement review and payment schedule alignment.",
        "Send updated software requirements document and confirm deployment dates.",
        "Quarterly review meeting to discuss project scope expansion and feedback.",
        "Client requested additional details on SLA terms and post-launch support.",
        "Call scheduled to clarify timeline dependencies and resource allocations.",
        "Brief check-in regarding client approval for the upcoming project release.",
    ]

    FOLLOWUP_CHANNELS = ["Call", "Email", "SMS", "Whatsapp"]

    @classmethod
    def generate_follow_up_data(cls) -> dict:
        """
        Generate authentic Indian business follow-up data.
        Returns:
            dict containing date (YYYY-MM-DD), time (HH:MM), channel, and realistic description.
        """
        # Select random future date (1 to 90 days ahead)
        future_date = datetime.now() + timedelta(days=random.randint(1, 90))
        date_str = future_date.strftime("%Y-%m-%d")

        # Select random business time (10:00 AM to 06:00 PM)
        hour = random.randint(10, 17)
        minute = random.choice([0, 15, 30, 45])
        time_str = f"{hour:02d}:{minute:02d}"

        channel = random.choice(cls.FOLLOWUP_CHANNELS)
        base_note = random.choice(cls.REALISTIC_FOLLOWUP_NOTES)
        unique_suffix = fake_in.numerify("#####")
        description = f"{base_note} (Ref: {unique_suffix})"

        return {
            "date": date_str,
            "time": time_str,
            "channel": channel,
            "description": description,
        }

    @classmethod
    def generate_lead_data(cls) -> dict:
        """
        Generate authentic Indian lead contact details.
        """
        first_name = fake_in.first_name()
        last_name = fake_in.last_name()
        full_name = f"{first_name} {last_name}"
        company_name = f"{fake_in.company()} India Pvt Ltd"
        email = f"{first_name.lower()}.{last_name.lower()}@{fake_in.free_email_domain()}"
        phone = fake_in.numerify("98########")
        city = fake_in.city()
        state = fake_in.state()

        return {
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "company_name": company_name,
            "email": email,
            "phone": phone,
            "city": city,
            "state": state,
        }
