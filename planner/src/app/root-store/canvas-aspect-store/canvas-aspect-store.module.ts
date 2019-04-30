import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import { feautureReducer } from './reducer';

@NgModule({
  declarations: [],
  imports: [CommonModule, StoreModule.forFeature('canvasAspect', feautureReducer)]
})
export class CanvasAspectStoreModule {}
