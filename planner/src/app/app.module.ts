import { HttpClientModule } from "@angular/common/http";
import { NgModule } from "@angular/core";
import { FlexLayoutModule } from "@angular/flex-layout";
import {
  MatButtonModule,
  MatIconModule,
  MatCardModule,
  MatToolbarModule,
  MatSidenavModule,
  MatListModule,
} from "@angular/material";
import { BrowserModule } from "@angular/platform-browser";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { RouterModule } from "@angular/router";

import { AppComponent } from "./app.component";
import { APP_ROUTES, BASE_URL } from "./app.routes";
import { RootStoreModule } from "./root-store";
import { CanvasAspectCardListComponent } from "./components/canvas-aspect-card-list/canvas-aspect-card-list.component";
import { CanvasAspectCardItemComponent } from "./components/canvas-aspect-card-item/canvas-aspect-card-item.component";
import { CanvasAspectsComponent } from "./containers/canvas-aspects/canvas-aspects.component";
import { HomeComponent } from "./containers/home/home.component";
import { NavbarComponent } from "./components/navbar/navbar.component";
import { CoreModule } from "./core/core.module";
import { ShouldLoginComponent } from "./containers/should-login/should-login.component";

@NgModule({
  declarations: [
    AppComponent,
    CanvasAspectCardListComponent,
    CanvasAspectCardItemComponent,
    CanvasAspectsComponent,
    NavbarComponent,
    HomeComponent,
    ShouldLoginComponent,
  ],
  imports: [
    BrowserModule,
    CoreModule.forRoot(),
    BrowserAnimationsModule,
    FlexLayoutModule,
    HttpClientModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatListModule,
    MatSidenavModule,
    MatToolbarModule,
    RootStoreModule,
    RouterModule.forRoot(APP_ROUTES),
  ],
  providers: [{ provide: BASE_URL, useValue: "http://localhost:8000" }],
  bootstrap: [AppComponent],
})
export class AppModule {}
