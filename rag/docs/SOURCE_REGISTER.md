# Source Register

Government sources collected for the SarkarSetu AI knowledge base.

## Collected official sources

| source_id | title | authority | source_url | topic | status | content_hash (SHA-256) |
|---|---|---|---|---|---|---|
| UDYAM_001 | Udyam Registration — Zero cost, No Fee and Free Registration of MSMEs (official portal page) | Ministry of MSME, Government of India | https://udyamregistration.gov.in/ | udyam_registration | collected · pending verification | 4c22342507ac9d8e8d43960cbad8e3e7a3f79bb1d9cf2a694225a444e360e9dc |
| MSME_001 | Ministry of MSME (homepage) | Ministry of MSME, Government of India | https://msme.gov.in/ | msme_classification | collected · pending verification | 043ba9565d65eff55e704ed109c9649a45836e1904ac27d9810086183de8e927 |
| GST_001 | GST Portal (homepage) | Central Board of Indirect Taxes & Customs (CBIC) / GSTN | https://www.gst.gov.in/ | gst_registration | collected · pending verification | c0df899bfd8876ca49ce4a8b0486baedcd5a905dd7357f078a32343c4cd6bde0 |
| MYSCHEME_001 | myScheme portal | Ministry of Electronics and Information Technology (MeitY), Government of India | https://www.myscheme.gov.in/ | msme_schemes | collected · pending verification | 2ac7277f99d4ea71f9c2a03a2a7470ff0510dbd5dfb7e2db3fcebbe94726aabd |

## Retrieval & verification metadata

- Retrieved at: 2026-11-08 (all sources)
- Publication date: not available from homepage (null)
- Version: not available (null)
- Verification status: **pending** for all sources — fetched from official government
  websites but NOT yet human-verified. None are presented as verified legal
  guidance.
- Extraction method: pdf_text (homepage HTML rendered to a text PDF for indexing)
- Page counts: UDYAM_001=4, MSME_001=1, GST_001=1, MYSCHEME_001=2

## Sources that could not be accessed

None. All four official URLs returned HTTP 200.

## Sources requiring manual verification

All four. The GST portal homepage returned a "Request Rejected" page (the portal
likely requires a session/JavaScript), so its content does not contain usable
GST registration guidance. A dedicated GST registration circular/PDF from
cbic-gst.gov.in or gst.gov.in should be manually collected before GST-related
reliance.

## Important extracted information (from authentic sources — pending verification)

UDYAM_001 (udyamregistration.gov.in) contains authentic MSME classification
thresholds (investment/turnover for micro/small/medium, pre & post 01-04-2025)
and states Udyam Registration is free, based on self-declaration, no renewal
needed, with a permanent registration number and dynamic QR-code certificate.

These figures appear on the official portal but must be cross-checked against
the latest official notification before being presented to users.

## Known limitations

- Homepages were crawled rather than specific scheme/registration PDFs; some
  pages (notably GST) returned generic/rejected content rather than detailed
  guidance. Manual collection of official registration PDFs/circulars is
  recommended.
- All sources are `verification_status=pending`; none are auto-verified merely
  for being on a government domain.
- Tesseract OCR binary is required for scanned-PDF OCR (verified working in
  this environment).
- Classification and field extraction are rule-based.

## Source freshness

Each source carries a SHA-256 `content_hash`. Re-collecting the same URL and
comparing hashes detects content changes (`SourceVersioning`). Age alone never
marks a source outdated; `verification_status` is updated by human review.
