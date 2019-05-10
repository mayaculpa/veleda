import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import { featureReducer } from './reducer';

@NgModule({
  declarations: [],
  imports: [CommonModule, StoreModule.forFeature('canvasAspect', featureReducer)]
})
export class CanvasAspectStoreModule {}
