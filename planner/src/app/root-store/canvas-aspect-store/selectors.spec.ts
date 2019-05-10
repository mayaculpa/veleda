import * as uuid from 'uuid';

import { CanvasAspect } from '../../models';
import { State } from './state';
import { selectAllCanvasAspectItems, selectCanvasAspectById } from './selectors';
import { EntityAdapter, createEntityAdapter } from '@ngrx/entity';

describe('Canvas aspect selector', () => {
  let adapter: EntityAdapter<CanvasAspect>;
  let initialState: State;
  const createCanvasAspects = (): CanvasAspect[] => [
    { id: uuid.v4(), type: 'Box' },
    { id: uuid.v4(), type: 'Circle' }
  ];

  beforeEach(() => {
    adapter = createEntityAdapter<CanvasAspect>();
    initialState = adapter.getInitialState();
  });

  it('should get all aspects', () => {
    const aspects = createCanvasAspects();
    const state = adapter.addAll(aspects, initialState);
    const result = selectAllCanvasAspectItems({ canvasAspect: state });

    expect(result).toEqual(aspects);
  });

  it('should get specified aspect', () => {
    const aspects = createCanvasAspects();
    const state = adapter.addAll(aspects, initialState);
    const result = selectCanvasAspectById(aspects[1].id)({ canvasAspect: state });

    expect(result).toBe(aspects[1]);
  });
});
