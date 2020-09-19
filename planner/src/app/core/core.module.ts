import {
  OAuthStorage,
  OAuthModule,
  AuthConfig,
  OAuthModuleConfig,
} from "angular-oauth2-oidc";
import { NgModule, ModuleWithProviders, Optional, SkipSelf } from "@angular/core";
import { HttpClientModule } from "@angular/common/http";
import { AuthService } from "./auth.service";
import { AuthGuard } from "./auth-guard.service";
import { AuthGuardWithForcedLogin } from "./auth-guard-with-forced-login.service";
import { authConfig } from "./auth.config";
import { authModuleConfig } from "./auth-module-config";

// We need a factory since localStorage is not available at AOT build time
export function storateFactory(): OAuthStorage {
  return localStorage;
}

@NgModule({
  imports: [HttpClientModule, OAuthModule.forRoot()],
  providers: [AuthService, AuthGuard, AuthGuardWithForcedLogin],
})
export class CoreModule {
  static forRoot(): ModuleWithProviders<CoreModule> {
    return {
      ngModule: CoreModule,
      providers: [
        { provide: AuthConfig, useValue: authConfig },
        { provide: OAuthModuleConfig, useValue: authModuleConfig },
        { provide: OAuthStorage, useFactory: storateFactory },
      ],
    };
  }

  constructor (@Optional() @SkipSelf() parentModule: CoreModule) {
    if(parentModule) {
      throw new Error("CoreModule is already loaded. Import it in the AppModule only.");
    }
  }
}
