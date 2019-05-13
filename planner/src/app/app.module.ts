import { NgModule } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatButtonModule, MatIconModule, MatCardModule, MatToolbarModule, MatSidenavModule, MatListModule } from '@angular/material';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';

import { AppComponent } from './app.component';
import { RootStoreModule } from './root-store';
import { CanvasAspectCardListComponent } from './components/canvas-aspect-card-list/canvas-aspect-card-list.component';
import { CanvasAspectCardItemComponent } from './components/canvas-aspect-card-item/canvas-aspect-card-item.component';
import { CanvasAspectsComponent } from './containers/canvas-aspects/canvas-aspects.component';
import { routes } from './app.routes';
import { NavbarComponent } from './components/navbar/navbar.component';
import { FloorPlannerComponent } from './containers/floor-planner/floor-planner.component';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { FabricCanvasComponent } from './components/fabric-canvas/fabric-canvas.component';

@NgModule({
  declarations: [
    AppComponent,
    CanvasAspectCardListComponent,
    CanvasAspectCardItemComponent,
    CanvasAspectsComponent,
    NavbarComponent,
    FloorPlannerComponent,
    FabricCanvasComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    FlexLayoutModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatListModule,
    MatSidenavModule,
    MatToolbarModule,
    RootStoreModule,
    RouterModule.forRoot(routes),
    StoreDevtoolsModule.instrument({
      maxAge: 20
    })
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
