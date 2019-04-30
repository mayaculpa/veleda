import { Actions, ActionTypes } from './actions';
import { featureAdapter, initialState, State } from './state';

export function feautureReducer(state = initialState, action: Actions): State {
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
