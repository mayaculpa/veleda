import { MemoizedSelector, createFeatureSelector, createSelector } from '@ngrx/store';

import { MetaAspect } from '../../models';
import { featureAdapter, State } from './state';

export const selectMetaAspectState: MemoizedSelector<object, State> = createFeatureSelector<
  State
>('metaAspect');

export const selectAllMetaAspectItems: (
  state: object
) => MetaAspect[] = featureAdapter.getSelectors(selectMetaAspectState).selectAll;

export const selectMetaAspectById = (id: string) =>
  createSelector(
    this.selectAllMetaAspectItems,
    (allMetaAspects: MetaAspect[]) => {
      if (allMetaAspects) {
        return allMetaAspects.find(p => p.id === id);
      } else {
        return null;
      }
    }
  );
