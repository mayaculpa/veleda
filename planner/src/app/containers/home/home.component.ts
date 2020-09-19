import { Component, OnInit } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { OAuthService } from "angular-oauth2-oidc";

@Component({
  selector: "app-home",
  templateUrl: "./home.component.html",
  styleUrls: ["./home.component.css"],
})
export class HomeComponent implements OnInit {
  loginFailed: boolean = false;
  userProfile: object;
  usePopup: boolean;
  login: false;

  constructor(
    private route: ActivatedRoute,
    private oauthService: OAuthService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(p => {
      this.login = p["login"];
    })
  }

  async loginCode() {
    
  }
}
