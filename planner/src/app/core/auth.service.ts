import { Injectable } from "@angular/core";
import {
  BehaviorSubject,
  ReplaySubject,
  Observable,
  combineLatest,
} from "rxjs";
import { filter, map } from "rxjs/operators";
import { OAuthService, OAuthErrorEvent } from "angular-oauth2-oidc";
import { Router } from "@angular/router";

@Injectable({ providedIn: "root" })
export class AuthService {
  private isAuthentivatedSubject$ = new BehaviorSubject<boolean>(false);
  public isAuthenticated$ = this.isAuthentivatedSubject$.asObservable();

  private isDoneLoadingSubject$ = new ReplaySubject<boolean>();
  public isDoneLoading$ = this.isDoneLoadingSubject$.asObservable();

  public canActivateProtectedRoutes$: Observable<boolean> = combineLatest([
    this.isAuthenticated$,
    this.isDoneLoading$,
  ]).pipe(map((values) => values.every((b) => b)));

  private navigateToLoginPage() {
    this.router.navigateByUrl("/should-login");
  }

  constructor(private oauthService: OAuthService, private router: Router) {
    this.oauthService.events.subscribe((event) => {
      if (event instanceof OAuthErrorEvent) {
        console.error("OAuthErrorEvent Object: ", event);
      } else {
        console.warn("OAuthEvent Object:", event);
      }
    });

    window.addEventListener("storage", (event) => {
      if (event.key !== "access_token" && event.key !== null) {
        return;
      }

      console.warn(
        "Noticed changes to access_token (most likely from another tab), updating isAuthenticated"
      );
      this.isAuthentivatedSubject$.next(
        this.oauthService.hasValidAccessToken()
      );

      if (!this.oauthService.hasValidAccessToken()) {
        this.navigateToLoginPage();
      }
    });

    this.oauthService.events.subscribe((_) => {
      this.isAuthentivatedSubject$.next(
        this.oauthService.hasValidAccessToken()
      );
    });

    // TODO: No OIDC service --> User custom API
    this.oauthService.events
      .pipe(filter((e) => ["token_received"].includes(e.type)))
      .subscribe((e) => this.oauthService.loadUserProfile());

    this.oauthService.events
      .pipe(
        filter((e) => ["session_terminated", "session_error"].includes(e.type))
      )
      .subscribe((e) => this.navigateToLoginPage());

    this.oauthService.setupAutomaticSilentRefresh();
  }

  public runInitialLoginSequence(): Promise<void> {
    // 1. SILENT LOGIN:
    // Try to log in via a refresh because then we can prevent
    // needing to redirect the user:
    return this.oauthService.tryLoginCodeFlow().then(() => {
      if (this.oauthService.hasValidAccessToken()) {
        return Promise.resolve();
      }

      return this.oauthService
        .silentRefresh()
        .then(() => Promise.resolve())
        .catch((result) => {
          // Subset of situations from https://openid.net/specs/openid-connect-core-1_0.html#AuthError
          // Only the ones where it's reasonably sure that sending the
          // user to the IdServer will help.
          const errorResponsesRequiringUserInteraction = [
            "interaction_required",
            "login_required",
            "account_selection_required",
            "consent_required",
          ];

          if (
            result &&
            result.reason &&
            errorResponsesRequiringUserInteraction.indexOf(
              result.reason.error
            ) >= 0
          ) {
            // 2. ASK FOR LOGIN:
            // At this point we know for sure that we have to ask the
            // user to log in, so we redirect them to the IdServer to
            // enter credentials.
            //
            // Enable this to ALWAYS force a user to login.
            // this.login();
            //
            // Instead, we'll now do this:
            console.warn(
              "User interaction is needed to log in, we will wait for the user to manually log in."
            );
            return Promise.resolve();
          }

          return Promise.reject(result);
        })
        .then(() => {
          this.isDoneLoadingSubject$.next(true);

          // Check for the strings 'undefined' and 'null' just to be sure. Our current
          // login(...) should never have this, but in case someone ever calls
          // initImplicitFlow(undefined | null) this could happen.
          if (
            this.oauthService.state &&
            this.oauthService.state !== "undefined" &&
            this.oauthService.state !== "null"
          ) {
            let stateUrl = this.oauthService.state;
            if (stateUrl.startsWith("/") === false) {
              stateUrl = decodeURIComponent(stateUrl);
            }
            console.log(
              `There was state of ${this.oauthService.state}, so we are sending you to: ${stateUrl}`
            );
            this.router.navigateByUrl(stateUrl);
          }
        })
        .catch(() => this.isDoneLoadingSubject$.next(true));
    });
  }

  public login(targetUrl?: string) {
    this.oauthService.initLoginFlow(targetUrl || this.router.url);
  }

  public logout() {
    this.oauthService.logOut();
  }
  public refresh() {
    this.oauthService.silentRefresh();
  }
  public hasValidToken() {
    return this.oauthService.hasValidAccessToken();
  }

  // These normally won't be exposed from a service like this, but
  // for debugging it makes sense.
  public get accessToken() {
    return this.oauthService.getAccessToken();
  }
  public get refreshToken() {
    return this.oauthService.getRefreshToken();
  }
  public get identityClaims() {
    return this.oauthService.getIdentityClaims();
  }
  public get idToken() {
    return this.oauthService.getIdToken();
  }
  public get logoutUrl() {
    return this.oauthService.logoutUrl;
  }
}
