"""Generate an original, fictional PDF fixture. Not real payer policy."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

out = Path(__file__).resolve().parents[1] / 'docs' / 'sample-training.pdf'
pages = [
    ('DEMO: Prior Authorization Policy',
     'FICTIONAL TRAINING DATA - NOT A REAL PAYER POLICY. '
     'The Meridian Learning Plan is an invented payer for testing this application. '
     'Prior authorization: advanced imaging requests must include a completed fictional '
     'authorization form and recent clinical notes from the ordering provider. '
     'Turnaround: standard requests are reviewed within five invented business days. '
     'Submit through the fictional Meridian Provider Learning Portal. '
     'This example has no real coverage, deadline, or connection to any insurance plan.'),
    ('DEMO: Timely Filing and Denial Code CO-29',
     'FICTIONAL TRAINING DATA - NOT A REAL PAYER POLICY. '
     'The Meridian Learning Plan is an invented payer for software testing. '
     'Timely filing: claims must be submitted within ninety invented days from the date of service. '
     'Denial code CO-29: the fictional code used when a claim arrives after the filing limit. '
     'Corrected claims: resubmit with the fictional frequency code 7 within the same invented window. '
     'Appeals: a written fictional appeal with supporting documents is required. '
     'No real policy, coverage, financial rule, or official approval is implied.')
]
c = canvas.Canvas(str(out))
c.setTitle('Fictional Payer Policies - Training Fixture')
for title, text in pages:
    c.setFillColorRGB(.09,.23,.37); c.setFont('Helvetica-Bold', 18)
    c.drawString(48, 785, title)
    c.setFont('Helvetica', 11)
    y = 745
    for line in simpleSplit(text, 'Helvetica', 11, 490):
        c.drawString(48, y, line); y -= 19
    c.drawString(48, 50, 'Synthetic test fixture. Not official information.')
    c.showPage()
c.save()
print(out)
