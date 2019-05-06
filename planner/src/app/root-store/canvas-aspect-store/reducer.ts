import { Actions, ActionTypes } from './actions';
import { featureAdapter, initialState, State } from './state';

export function featureReducer(state = initialState, action: Actions): State {
  switch (action.type) {
    case ActionTypes.ADD: {
      return featureAdapter.addMany(action.payload.items, state);
    }
    case ActionTypes.REMOVE: {
      return featureAdapter.removeMany(action.payload.ids, state);
    }
    default: {
      return state;
    }
  }
}
