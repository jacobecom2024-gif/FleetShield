# Zero-upfront deployment gate

FleetShield must not be deployed merely to make a cloud claim. Deployment is
allowed only after hackathon credits or an already-funded Google Cloud billing
account are visible and the user has accepted that Google Cloud budgets are alerts,
not hard spending caps.

## Required services

- Cloud Run
- Artifact Registry
- Cloud Build
- Firestore Native mode
- Vertex AI / Gemini
- Pub/Sub
- Cloud Logging and Trace

## Cost containment

The checked-in Cloud Build configuration applies:

- zero minimum instances;
- one maximum instance;
- one CPU and 512 MiB memory;
- 20-request concurrency;
- 60-second request timeout;
- no external paid API dependency.

These limits reduce exposure but do not mathematically guarantee a zero invoice.
Create a low budget alert before deployment and remove the service after judging if
there is no continuing need.

## Deployment prerequisites

1. A Google Cloud project dedicated to FleetShield.
2. Hackathon credits or explicit confirmation that billing exposure is acceptable.
3. Artifact Registry repository named `fleetshield` in `europe-west1`.
4. Firestore database in Native mode.
5. Cloud Run service account with least-privilege Vertex AI User and scoped
   Firestore access.

## Build and deploy

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=europe-west1
```

After deployment, collect evidence before making any submission claim:

```bash
curl -s "$SERVICE_URL/api/health"
curl -s -X POST "$SERVICE_URL/api/demo" \
  -H 'content-type: application/json' -d '{}'
```

The production evidence is acceptable only when:

- policy `discovered_from` begins with `google-adk:gemini:multi-agent:`;
- `/api/evidence` reports `google_adk_executed` and `cloud_run_active` as true;
- if Firestore is claimed as live, `firestore_active` must also be true;
- vulnerable effects equal 2;
- protected effects equal 1;
- protected blocked actions equal 1;
- protected `safe` equals true;
- a matching Firestore experiment document and Cloud Run revision exist.

## Honest fallback

If credits or credentials are unavailable, submit the reproducible local proof only
if the rules permit it. Do not describe documented Firestore or Pub/Sub adapters as
live production integrations.
