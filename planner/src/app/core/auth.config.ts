import { AuthConfig } from "angular-oauth2-oidc";

export const authConfig: AuthConfig = {
  issuer: "http://127.0.0.1:8000",
  redirectUri: "http://127.0.0.1:4200/",
  clientId: "TA8O3iYh7z8T4zi52scxGEdDbprlhmJbK9eMKIjK",
  loginUrl: "http://127.0.0.1:8000/o/authorize/",
  scope: "userinfo-v1",
  oidc: false,
  disablePKCE: true,
  requestAccessToken: true,
  tokenEndpoint: "http://127.0.0.1:8000/o/token/",
  userinfoEndpoint: "http://127.0.0.1:8000/api/v1/userinfo/",
  responseType: "code",
  requireHttps: false
};
