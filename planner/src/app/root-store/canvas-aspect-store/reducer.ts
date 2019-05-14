import { Actions, ActionTypes } from './actions';
import { featureAdapter, initialState, State } from './state';

export function featureReducer(state = initialState, action: Actions): State {
  switch (action.type) {
    case ActionTypes.ADD: {
      const newState = featureAdapter.addMany(action.payload.items, state);
      newState.addedIds = action.payload.items.map(item => item.id);
      newState.changedIds = [];
      newState.removedIds = [];
      return newState;
    }
    case ActionTypes.REMOVE: {
      const newState = featureAdapter.removeMany(action.payload.ids, state);
      newState.addedIds = [];
      newState.changedIds = [];
      newState.removedIds = action.payload.ids;
      return newState;
    }
    default: {
      return state;
    }
  }
}
