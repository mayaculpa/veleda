import * as uuid from 'uuid';

import { CanvasAspect } from '../../models';
import { featureAdapter, initialState } from './state';
import { selectAllCanvasAspectItems, selectCanvasAspectById } from './selectors';

describe('Canvas aspect selector', () => {
  const createCanvasAspects = (): CanvasAspect[] => [
    { id: uuid.v4(), type: 'Box' },
    { id: uuid.v4(), type: 'Circle' }
  ];

  it('should get all aspects', () => {
    const aspects = createCanvasAspects();
    const state = featureAdapter.addAll(aspects, initialState);
    const result = selectAllCanvasAspectItems({ canvasAspect: state });

    expect(result).toEqual(aspects);
  });

  it('should get specified aspect', () => {
    const aspects = createCanvasAspects();
    const state = featureAdapter.addAll(aspects, initialState);
    const result = selectCanvasAspectById(aspects[1].id)({ canvasAspect: state });

    expect(result).toBe(aspects[1]);
  });
});
