#!/bin/bash

echo "==================================="
echo "AI Intelligence MongoDB Setup"
echo "==================================="
echo ""

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please run ./install.sh first."
        exit 1
    fi
fi

echo "✓ Virtual environment active"
echo ""

# Check if pymongo and tinydb are installed
echo "Checking dependencies..."
python -c "import pymongo, tinydb" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install pymongo tinydb
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Ask user for MongoDB preference
echo "==================================="
echo "MongoDB Setup Options"
echo "==================================="
echo ""
echo "1. Use TinyDB (recommended for development)"
echo "   - No setup required"
echo "   - Works immediately"
echo "   - Stores data in local JSON file"
echo ""
echo "2. MongoDB Atlas (recommended for production)"
echo "   - Free tier available"
echo "   - Cloud-hosted"
echo "   - Requires account setup"
echo ""
echo "3. Local MongoDB with Docker"
echo "   - Requires Docker installed"
echo "   - Runs on localhost"
echo ""
echo "4. Custom MongoDB URI"
echo "   - Use existing MongoDB server"
echo ""

read -p "Choose option (1-4) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "✓ Using TinyDB (no additional setup needed)"
        echo ""
        echo "Data will be stored in: data/ai/intelligence.json"
        mkdir -p data/ai
        ;;
    2)
        echo ""
        echo "==================================="
        echo "MongoDB Atlas Setup"
        echo "==================================="
        echo ""
        echo "Follow these steps:"
        echo "1. Go to https://www.mongodb.com/cloud/atlas"
        echo "2. Sign up for a free account"
        echo "3. Create a new cluster (M0 Free tier)"
        echo "4. Create a database user"
        echo "5. Whitelist your IP address (or 0.0.0.0/0 for testing)"
        echo "6. Get your connection string (should look like:"
        echo "   mongodb+srv://username:password@cluster.mongodb.net/)"
        echo ""
        read -p "Enter your MongoDB Atlas URI: " mongo_uri
        
        if [ -n "$mongo_uri" ]; then
            # Test connection
            echo ""
            echo "Testing connection..."
            python -c "
from pymongo import MongoClient
try:
    client = MongoClient('$mongo_uri', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ Connection successful!')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" || exit 1
            
            # Save to .env file
            echo "" >> .env
            echo "# MongoDB Configuration" >> .env
            echo "MONGODB_URI=\"$mongo_uri\"" >> .env
            echo ""
            echo "✓ MongoDB URI saved to .env file"
        else
            echo "❌ No URI provided. Falling back to TinyDB."
        fi
        ;;
    3)
        echo ""
        echo "==================================="
        echo "Docker MongoDB Setup"
        echo "==================================="
        echo ""
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker is not installed."
            echo "Please install Docker first: https://docs.docker.com/get-docker/"
            exit 1
        fi
        
        # Check if MongoDB container exists
        if docker ps -a | grep -q mongodb_ai; then
            echo "MongoDB container already exists."
            read -p "Remove and recreate? (y/N): " recreate
            if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
                docker rm -f mongodb_ai
            else
                docker start mongodb_ai
                mongo_uri="mongodb://admin:password@localhost:27017/"
            fi
        fi
        
        if [ -z "$mongo_uri" ]; then
            echo "Creating MongoDB container..."
            docker run -d \
                --name mongodb_ai \
                -p 27017:27017 \
                -e MONGO_INITDB_ROOT_USERNAME=admin \
                -e MONGO_INITDB_ROOT_PASSWORD=password \
                -v mongodb_ai_data:/data/db \
                mongo:latest
            
            echo "Waiting for MongoDB to start..."
            sleep 5
            
            mongo_uri="mongodb://admin:password@localhost:27017/"
            
            # Test connection
            echo "Testing connection..."
            python -c "
from pymongo import MongoClient
try:
    client = MongoClient('$mongo_uri', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ Connection successful!')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" || exit 1
            
            # Save to .env file
            echo "" >> .env
            echo "# MongoDB Configuration" >> .env
            echo "MONGODB_URI=\"$mongo_uri\"" >> .env
            echo ""
            echo "✓ MongoDB running on Docker"
            echo "✓ URI saved to .env file"
        fi
        ;;
    4)
        echo ""
        read -p "Enter your MongoDB URI: " mongo_uri
        
        if [ -n "$mongo_uri" ]; then
            # Test connection
            echo ""
            echo "Testing connection..."
            python -c "
from pymongo import MongoClient
try:
    client = MongoClient('$mongo_uri', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ Connection successful!')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" || exit 1
            
            # Save to .env file
            echo "" >> .env
            echo "# MongoDB Configuration" >> .env
            echo "MONGODB_URI=\"$mongo_uri\"" >> .env
            echo ""
            echo "✓ MongoDB URI saved to .env file"
        else
            echo "❌ No URI provided. Falling back to TinyDB."
        fi
        ;;
    *)
        echo "Invalid option. Using TinyDB."
        ;;
esac

echo ""
echo "==================================="
echo "Testing AI Intelligence System"
echo "==================================="
echo ""

python test_ai_intelligence.py

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "✓ Setup Complete!"
    echo "==================================="
    echo ""
    echo "Your AI Intelligence system is ready to use!"
    echo ""
    echo "Documentation: AI_INTELLIGENCE_SETUP.md"
    echo "Configuration: data/config/ai_config.json"
    echo ""
    if [ -n "$mongo_uri" ]; then
        echo "Backend: MongoDB"
        echo "URI: $mongo_uri"
    else
        echo "Backend: TinyDB"
        echo "Data file: data/ai/intelligence.json"
    fi
    echo ""
    echo "To use in your code:"
    echo "  from src.ai_intelligence import get_ai_intelligence"
    echo "  ai = get_ai_intelligence()"
    echo ""
else
    echo ""
    echo "❌ Setup test failed. Please check the error messages above."
    exit 1
fi
