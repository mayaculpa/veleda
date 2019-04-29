
### STAGE 1: Build ###

# We label our stage as ‘builder’
FROM node:10-alpine as builder


## Storing node modules on a separate layer will prevent unnecessary npm installs at each build
WORKDIR /tmp
COPY package.json package-lock.json /tmp/
# Slow npm install to avoid network congestion in Gründervilla, BS, DE
RUN npm set maxsockets 1 && npm install
RUN mkdir -p /planner && mv /tmp/node_modules /planner/node_modules

## Build the angular app in production mode and store the artifacts in dist folder
WORKDIR /planner
COPY . .
RUN npm run ng build -- --prod --output-path=dist


# ### STAGE 2: Setup ###

FROM nginx:1.14.1-alpine

## Copy our default nginx config
COPY nginx/default.conf /etc/nginx/conf.d/

## Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

## From ‘builder’ stage copy over the artifacts in dist folder to default nginx public folder
COPY --from=builder /planner/dist /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]

