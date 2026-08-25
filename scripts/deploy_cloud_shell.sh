#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:-fleetshield-agentic}"
REGION="${REGION:-europe-west1}"
VERTEX_LOCATION="${VERTEX_LOCATION:-global}"
SERVICE="fleetshield"
REPOSITORY="fleetshield"
RUNTIME_SA="fleetshield-runtime"
RUNTIME_SA_EMAIL="${RUNTIME_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/app:submission"

if [[ "${PROJECT_ID}" != "fleetshield-agentic" ]]; then
  echo "Refusing to deploy outside the dedicated FleetShield project." >&2
  exit 2
fi

gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  run.googleapis.com \
  aiplatform.googleapis.com \
  pubsub.googleapis.com \
  logging.googleapis.com

if ! gcloud artifacts repositories describe "${REPOSITORY}" \
  --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPOSITORY}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="FleetShield submission images"
fi

if ! gcloud iam service-accounts describe "${RUNTIME_SA_EMAIL}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${RUNTIME_SA}" \
    --display-name="FleetShield Cloud Run runtime"
fi

for role in roles/aiplatform.user roles/datastore.user; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${RUNTIME_SA_EMAIL}" \
    --role="${role}" \
    --condition=None >/dev/null
done

if ! gcloud firestore databases describe --database='(default)' >/dev/null 2>&1; then
  gcloud firestore databases create \
    --database='(default)' \
    --location="${REGION}" \
    --type=firestore-native
fi

if ! gcloud pubsub topics describe fleetshield-events >/dev/null 2>&1; then
  gcloud pubsub topics create fleetshield-events
fi

python -m unittest discover -s tests -v
gcloud builds submit --tag "${IMAGE}" .

gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="${RUNTIME_SA_EMAIL}" \
  --allow-unauthenticated \
  --min=0 \
  --max=1 \
  --cpu=1 \
  --memory=512Mi \
  --concurrency=20 \
  --timeout=60 \
  --set-env-vars="GEMINI_MODEL=gemini-3.5-flash,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${VERTEX_LOCATION},FLEETSHIELD_STATE_BACKEND=firestore"

SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo "SERVICE_URL=${SERVICE_URL}"
curl --fail --silent --show-error "${SERVICE_URL}/api/health"
echo
curl --fail --silent --show-error -X POST "${SERVICE_URL}/api/demo" \
  -H 'content-type: application/json' -d '{}'
echo

