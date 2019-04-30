import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import { feautureReducer } from './reducer';

@NgModule({
  declarations: [],
  imports: [CommonModule, StoreModule.forFeature('metaAspect', feautureReducer)]
})
export class MetaAspectStoreModule {}
