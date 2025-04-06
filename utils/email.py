# utils/email.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email(subject, to_email, template_name, context):
    """
    Generic email sending function
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        None,  # Uses DEFAULT_FROM_EMAIL from settings
        [to_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()