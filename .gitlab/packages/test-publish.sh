#!/bin/bash
# Local test script for package publishing

# Copy the npm package definition to package.json
cp mapbox-gl.npm package.json

# Check if the copy was successful
if [ ! -f package.json ]; then
  echo "Failed to create package.json"
  exit 1
fi

echo "Package.json created successfully"
echo "Contents:"
cat package.json

echo -e "\nTo publish this package to GitLab, you would need to:"
echo "1. Set up credentials in .npmrc"
echo "2. Run 'npm publish'"
echo "3. Check your GitLab Package Registry at https://gitlab.com/gitlab-da/sugaroverflow/weather-app/-/packages" 