import { OAuthModuleConfig } from 'angular-oauth2-oidc';

export const authModuleConfig: OAuthModuleConfig = {
  resourceServer: {
    allowedUrls: ['http://127.0.0.1:8000/api'],
    sendAccessToken: true,
  }
};