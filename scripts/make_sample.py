"""Generate an original, fictional PDF fixture. Not government guidance."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

out = Path(__file__).resolve().parents[1] / 'docs' / 'sample-training.pdf'
pages = [
    ('DEMO: Seed Learning Grant',
     'FICTIONAL TRAINING DATA - NOT A GOVERNMENT SCHEME. '
     'The Seed Learning Grant is an invented scheme for testing this application. '
     'Eligibility: participants must belong to the fictional Green Village Learning Club. '
     'Benefit: a demonstration seed kit and one training session. '
     'Application documents: club membership card and a completed training form. '
     'Apply at the fictional Green Village Training Desk. No payment is required. '
     'This example has no real deadline, subsidy amount, or government connection.'),
    ('DEMO: Drip Irrigation Workshop',
     'FICTIONAL TRAINING DATA - NOT A GOVERNMENT SCHEME. '
     'The Drip Irrigation Workshop is a second invented scheme for software testing. '
     'Eligibility: registered members of the fictional Water Learning Group. '
     'Benefit: a two-day drip irrigation workshop, not an equipment subsidy. '
     'Required documents: workshop registration form. '
     'Apply at the fictional Water Learning Group office. '
     'No real policy, eligibility, financial benefit, or official approval is implied.')
]
c = canvas.Canvas(str(out))
c.setTitle('Fictional Agriculture Schemes - Training Fixture')
for title, text in pages:
    c.setFillColorRGB(.08,.24,.16); c.setFont('Helvetica-Bold', 18)
    c.drawString(48, 785, title)
    c.setFont('Helvetica', 11)
    y = 745
    for line in simpleSplit(text, 'Helvetica', 11, 490):
        c.drawString(48, y, line); y -= 19
    c.drawString(48, 50, 'Synthetic test fixture. Not official information.')
    c.showPage()
c.save()
print(out)
