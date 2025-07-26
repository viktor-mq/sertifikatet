#!/bin/bash

# Build CSS for production
echo "🎨 Building Tailwind CSS for production..."
npm run build-css-prod

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ CSS build completed successfully!"
    echo "📦 Generated: static/css/tailwind.css"
    echo "📊 File size: $(ls -lah static/css/tailwind.css | awk '{print $5}')"
else
    echo "❌ CSS build failed!"
    exit 1
fi