# Use the official Node.js image as the base image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the rest of the application code
COPY . .

# Build the React application
RUN npm run build

# Install a simple server to serve the build files
RUN npm install -g serve

# Expose the port that the app runs on
EXPOSE 3000

# Command to run the application
CMD ["serve", "-s", "build"]
