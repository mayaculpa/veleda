import { Routes } from "@angular/router";
import { CanvasAspectsComponent } from "./containers/canvas-aspects/canvas-aspects.component";
import { InjectionToken } from "@angular/core";
import { HomeComponent } from "./containers/home/home.component";
import { ShouldLoginComponent } from './containers/should-login/should-login.component';

export const APP_ROUTES: Routes = [
  {
    path: "",
    redirectTo: "home",
    pathMatch: "full",
  },
  {
    path: "home",
    component: HomeComponent,
  },
  {
    path: "build",
    component: CanvasAspectsComponent,
  },
  {
    path: "should-login", component: ShouldLoginComponent
  },
  {
    path: "**",
    redirectTo: "home",
  },
];

export const BASE_URL = new InjectionToken<string>("BASE_URL");
