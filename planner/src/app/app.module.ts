import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { RootStoreModule } from './root-store';

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    RootStoreModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
