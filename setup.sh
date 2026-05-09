#!/bin/bash
# Setup script for Chhapadiya project

echo "🚀 Chhapadiya Project Setup"
echo "================================"

# Check if .env exists
if [ -f .env ]; then
    echo "✓ .env file already exists"
else
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env created. Please edit it with your credentials."
fi

# Check if python-dotenv is installed
echo ""
echo "📦 Checking dependencies..."
pip list | grep python-dotenv > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ python-dotenv is installed"
else
    echo "📥 Installing python-dotenv..."
    pip install python-dotenv
fi

# Check if all required env vars are set
echo ""
echo "🔍 Checking environment variables..."

check_env() {
    if grep -q "^$1=" .env; then
        value=$(grep "^$1=" .env | cut -d'=' -f2)
        if [ "$value" != "<your-*>" ] && [ ! -z "$value" ]; then
            echo "✓ $1 is set"
            return 0
        fi
    fi
    echo "⚠ $1 is not set or is a placeholder"
    return 1
}

check_env "GOOGLE_CLIENT_ID"
check_env "GOOGLE_CLIENT_SECRET"
check_env "EMAIL_HOST_USER"
check_env "EMAIL_HOST_PASSWORD"

echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your actual credentials"
echo "2. Run: python manage.py setup_google_oauth"
echo "3. Run: python manage.py runserver"
echo ""
echo "📚 For detailed setup instructions, see ENV_SETUP_GUIDE.md"
echo "================================"
