import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { MatButtonModule, MatIconModule, MatCardModule } from '@angular/material';

import { AppComponent } from './app.component';
import { RootStoreModule } from './root-store';
import { CanvasAspectCardListComponent } from './components/canvas-aspect-card-list/canvas-aspect-card-list.component';
import { CanvasAspectCardItemComponent } from './components/canvas-aspect-card-item/canvas-aspect-card-item.component';
import { CanvasAspectsComponent } from './containers/canvas-aspects/canvas-aspects.component';

@NgModule({
  declarations: [
    AppComponent,
    CanvasAspectCardListComponent,
    CanvasAspectCardItemComponent,
    CanvasAspectsComponent
  ],
  imports: [
    BrowserModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    RootStoreModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
