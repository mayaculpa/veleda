import { EntityAdapter, createEntityAdapter } from '@ngrx/entity';
import * as uuid from 'uuid';

import { MetaAspect } from '../../models';
import { State } from './state';
import { selectAllMetaAspectItems, selectMetaAspectById } from './selectors';

describe('Meta aspect selector', () => {
  let adapter: EntityAdapter<MetaAspect>;
  let initialState: State;
  const createMetaAspects = (): MetaAspect[] => [
    { id: uuid.v4(), name: 'Box' },
    { id: uuid.v4(), name: 'Circle' }
  ];

  beforeEach(() => {
    adapter = createEntityAdapter<MetaAspect>();
    initialState = adapter.getInitialState();
  });

  it('should get all aspects', () => {
    const aspects = createMetaAspects();
    const state = adapter.addAll(aspects, initialState);
    const result = selectAllMetaAspectItems({ metaAspect: state });

    expect(result).toEqual(aspects);
  });

  it('should get specified aspect', () => {
    const aspects = createMetaAspects();
    const state = adapter.addAll(aspects, initialState);
    const result = selectMetaAspectById(aspects[1].id)({ metaAspect: state });

    expect(result).toBe(aspects[1]);
  });
});
