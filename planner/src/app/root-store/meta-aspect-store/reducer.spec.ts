import * as uuid from 'uuid';

import * as Actions from './actions';
import { initialState } from './state';
import { featureReducer } from './reducer';
import { MetaAspect } from '../../models';

describe('Meta aspect reducer', () => {
  const createMetaAspects = (): MetaAspect[] => [
    { id: uuid.v4(), name: '1st name' },
    { id: uuid.v4(), name: '2nd name' }
  ];

  it('should return init state', () => {
    const action = { type: 'NOOP' } as any;
    const result = featureReducer(undefined, action);

    expect(result).toBe(initialState);
  });

  it('should add items', () => {
    const aspects = createMetaAspects();
    const action = new Actions.AddAction({ items: aspects });
    const result = featureReducer(undefined, action);

    expect(result).toEqual({
      ...initialState,
      entities: {
        [aspects[0].id]: aspects[0],
        [aspects[1].id]: aspects[1]
      },
      ids: aspects.map(metaAspect => metaAspect.id)
    });
  });

  it('should add to existing items', () => {
    const firstSet = createMetaAspects();
    const secondSet = createMetaAspects();

    const firstAction = new Actions.AddAction({ items: firstSet });
    const firstResult = featureReducer(undefined, firstAction);
    const secondAction = new Actions.AddAction({ items: secondSet });
    const secondResult = featureReducer(firstResult, secondAction);

    expect(secondResult).toEqual({
      ...initialState,
      entities: {
        [firstSet[0].id]: firstSet[0],
        [firstSet[1].id]: firstSet[1],
        [secondSet[0].id]: secondSet[0],
        [secondSet[1].id]: secondSet[1]
      },
      ids: firstSet
        .map(metaAspect => metaAspect.id)
        .concat(secondSet.map(metaAspect => metaAspect.id))
    });
  });

  it('should remove an item', () => {
    const aspects = createMetaAspects();
    const idToRemove = aspects[0].id;

    const addAction = new Actions.AddAction({ items: aspects });
    const firstResult = featureReducer(undefined, addAction);
    const removeAction = new Actions.RemoveAction({ ids: [idToRemove] });
    const secondsResult = featureReducer(firstResult, removeAction);

    expect(secondsResult).toEqual({
      ...initialState,
      entities: {
        [aspects[1].id]: aspects[1]
      },
      ids: aspects.map(aspect => aspect.id).filter(id => id !== idToRemove)
    });
  });
});
