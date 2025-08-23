#!/bin/bash

# SpendCast Backend Deployment Script
# Deploys FastAPI application to Google Cloud Run

# Set the application name as a variable for backend
APP_NAME="spendcast-backend"

# Set project ID
PROJECT_ID="spendcast-backend"

# Export the tag with the current date and time
export TAG=$(date +%Y%m%d_%H%M%S)

# Function to handle failure and exit
handle_failure() {
    echo "❌ Error occurred during $1. Exiting script."
    exit 1
}

# Function to check if gcloud is authenticated
check_gcloud_auth() {
    echo "🔍 Checking gcloud authentication..."
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo "❌ Not authenticated with gcloud. Please run: gcloud auth login"
        exit 1
    fi
    echo "✅ gcloud authentication verified"
}

# Function to set the project
set_project() {
    echo "🔧 Setting gcloud project to $PROJECT_ID..."
    gcloud config set project $PROJECT_ID || handle_failure "setting gcloud project"
    echo "✅ Project set to $PROJECT_ID"
}

# Function to enable required APIs
enable_apis() {
    echo "🔧 Enabling required Google Cloud APIs..."
    gcloud services enable cloudbuild.googleapis.com || handle_failure "enabling Cloud Build API"
    gcloud services enable run.googleapis.com || handle_failure "enabling Cloud Run API"
    gcloud services enable containerregistry.googleapis.com || handle_failure "enabling Container Registry API"
    echo "✅ APIs enabled successfully"
}

# Print welcome message
echo "🚀 SpendCast Backend Deployment to Google Cloud Run"
echo "=================================================="
echo "Application: $APP_NAME"
echo "Project ID: $PROJECT_ID"
echo "Tag: $TAG"
echo ""

# Check prerequisites
check_gcloud_auth
set_project
enable_apis

# Ask user for build method
echo "Choose build method:"
echo "1) Local Docker build (requires Docker)"
echo "2) Google Cloud Build (recommended)"
read -p "Enter your choice (1 or 2): " BUILD_METHOD

if [ "$BUILD_METHOD" = "1" ]; then
    # Local Docker build with buildx
    echo "🔨 Building Docker image locally for $APP_NAME..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
    
    docker buildx build --no-cache --platform linux/amd64 -t $APP_NAME:$TAG --load . || handle_failure "Local Docker build"
    
    echo "🏷️  Tagging Docker image..."
    docker tag $APP_NAME:$TAG gcr.io/$PROJECT_ID/$APP_NAME:$TAG || handle_failure "Docker tagging"
    
    echo "📤 Pushing Docker image to Google Container Registry..."
    docker push gcr.io/$PROJECT_ID/$APP_NAME:$TAG || handle_failure "Docker push"
    
elif [ "$BUILD_METHOD" = "2" ]; then
    # Google Cloud Build
    echo "🔨 Building Docker image for $APP_NAME using Google Cloud Build..."
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$APP_NAME:$TAG . || handle_failure "Google Cloud Build"
    
else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi

# Load environment variables from env.production file
echo ""
echo "🔧 Loading environment variables from env.production file..."

ENV_VARS_FLAG=""
if [ -f "env.production" ]; then
    echo "✅ Found env.production file"
    
    # Read env.production and convert to Cloud Run format
    ENV_VARS=""
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip empty lines and comments
        if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Remove any leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Skip if key or value is empty
        if [[ -z "$key" || -z "$value" ]]; then
            continue
        fi
        
        echo "📝 Adding environment variable: $key"
        
        if [ -z "$ENV_VARS" ]; then
            ENV_VARS="$key=$value"
        else
            ENV_VARS="$ENV_VARS,$key=$value"
        fi
    done < env.production
    
    if [ ! -z "$ENV_VARS" ]; then
        ENV_VARS_FLAG="--set-env-vars $ENV_VARS"
        echo "✅ Loaded environment variables from env.production"
    else
        echo "⚠️  No valid environment variables found in env.production"
    fi
else
    echo "⚠️  env.production file not found. Would you like to set environment variables manually? (y/n)"
    read -p "Choice: " SET_ENV_VARS_MANUAL
    
    if [ "$SET_ENV_VARS_MANUAL" = "y" ] || [ "$SET_ENV_VARS_MANUAL" = "Y" ]; then
        echo "Enter environment variables (e.g., GRAPHDB_URL=http://localhost:7200/repositories/spendcast):"
        echo "Press Enter without input when done."
        
        ENV_VARS=""
        while true; do
            read -p "Environment variable: " ENV_VAR
            if [ -z "$ENV_VAR" ]; then
                break
            fi
            if [ -z "$ENV_VARS" ]; then
                ENV_VARS="$ENV_VAR"
            else
                ENV_VARS="$ENV_VARS,$ENV_VAR"
            fi
        done
        
        if [ ! -z "$ENV_VARS" ]; then
            ENV_VARS_FLAG="--set-env-vars $ENV_VARS"
        fi
    fi
fi

# Deploy to Google Cloud Run
echo ""
echo "🚀 Deploying $APP_NAME to Google Cloud Run..."
gcloud run deploy $APP_NAME \
    --image gcr.io/$PROJECT_ID/$APP_NAME:$TAG \
    --platform managed \
    --region europe-west3 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 100 \
    $ENV_VARS_FLAG \
    --revision-suffix=$(date +%s) || handle_failure "Google Cloud Run deployment"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $APP_NAME --region=europe-west3 --format="value(status.url)")

echo ""
echo "🎉 $APP_NAME deployment completed successfully!"
echo "==============================================="
echo "🌐 Service URL: $SERVICE_URL"
echo "📚 API Documentation: $SERVICE_URL/docs"
echo "🔍 Health Check: $SERVICE_URL/health"
echo "📊 Database Check: $SERVICE_URL/api/v1/database/check"
echo ""
echo "📋 Useful commands:"
echo "  View logs: gcloud run services logs read $APP_NAME --region=europe-west3"
echo "  Delete service: gcloud run services delete $APP_NAME --region=europe-west3"
echo "  Update traffic: gcloud run services update-traffic $APP_NAME --to-latest --region=europe-west3"