import { createEntityAdapter, EntityAdapter, EntityState } from '@ngrx/entity';
import { CanvasAspect } from '../../models';

export const featureAdapter: EntityAdapter<CanvasAspect> = createEntityAdapter<
  CanvasAspect
>();

export interface State extends EntityState<CanvasAspect> {}

export const initialState: State = featureAdapter.getInitialState();
