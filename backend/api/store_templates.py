from backend.models.template_model import save_template

# ✅ Store Sample Templates
save_template("Appointment Confirmation", "Your Appointment", "Hello [Name], your appointment is on [Date].")
save_template("Payment Inquiry", "Payment Details", "Hello [Name], your payment of [Amount] is pending.")
print("✅ Templates stored in MongoDB!")
