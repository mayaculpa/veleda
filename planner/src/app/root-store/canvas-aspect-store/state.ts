import { createEntityAdapter, EntityAdapter, EntityState } from '@ngrx/entity';
import { CanvasAspect } from '../../models';

export const featureAdapter: EntityAdapter<CanvasAspect> = createEntityAdapter<CanvasAspect>();

export interface State extends EntityState<CanvasAspect> {
  addedIds: string[];
  changedIds: string[];
  removedIds: string[];
}

export const initialState: State = featureAdapter.getInitialState({
  addedIds: [],
  changedIds: [],
  removedIds: []
});
