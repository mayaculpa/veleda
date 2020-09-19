import { Component, OnInit } from '@angular/core';
import { OAuthService } from 'angular-oauth2-oidc';

@Component({
  selector: 'app-should-login',
  templateUrl: './should-login.component.html',
  styleUrls: ['./should-login.component.css']
})
export class ShouldLoginComponent {

  constructor(private authService: OAuthService) { }

  public login($event) {
    $event.preventDefault();
    this.authService.initLoginFlow();
  }

}
