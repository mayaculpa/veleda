import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CanvasAspectStoreModule } from './canvas-aspect-store/canvas-aspect-store.module';
import { MetaAspectStoreModule } from './meta-aspect-store/meta-aspect-store.module';
import { StoreModule } from '@ngrx/store';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    CanvasAspectStoreModule,
    MetaAspectStoreModule,
    StoreModule.forRoot({})
  ]
})
export class RootStoreModule { }
