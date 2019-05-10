import { createEntityAdapter, EntityAdapter, EntityState } from '@ngrx/entity';
import { MetaAspect } from '../../models';

export const featureAdapter: EntityAdapter<MetaAspect> = createEntityAdapter<
  MetaAspect
>();

export interface State extends EntityState<MetaAspect> {}

export const initialState: State = featureAdapter.getInitialState();
