import smtplib
from email.message import EmailMessage
 
def send_approval_email(submission):
    msg = EmailMessage()
    msg["Subject"] = "Approval Needed"
    msg["From"] = submission.sender_email
    msg["To"] = submission.approver_email
 
    download_link = f"http://localhost:8000/download/{submission.id}"
    approve_link = f"http://localhost:8000/email/decision/{submission.id}/approve"
    refer_link = f"http://localhost:8000/email/decision/{submission.id}/refer"
 
    msg.add_alternative(f"""
    <html>
        <body>
            <p>Hi,<br><br>
            A file '<strong>{submission.filename}</strong>' has been sent for your approval.<br>
            <a href='{download_link}'>Download File</a><br><br>
            <a href='{approve_link}'>Approve</a> | <a href='{refer_link}'>Refer Back</a>
            </p>
        </body>
    </html>
    """, subtype='html')
 
    with open(submission.filepath, "rb") as f:
        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=submission.filename)
 
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(submission.sender_email, submission.sender_password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending approval email: {e}")
 
def notify_sender(submission):
    msg = EmailMessage()
    msg["Subject"] = f"Your file '{submission.filename}' was {submission.status}"
    msg["From"] = submission.approver_email
    msg["To"] = submission.sender_email
 
    msg.set_content(f"Hi,\n\nYour file '{submission.filename}' was {submission.status.lower()} by the approver.")
 
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(submission.sender_email, submission.sender_password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error notifying sender: {e}")