import { Action } from '@ngrx/store';
import { MetaAspect } from '../../models';

export enum ActionTypes {
  ADD = '[MetaAspect] Add',
  REMOVE = '[MetaAspect] Remove'
}

export class AddAction implements Action {
  readonly type = ActionTypes.ADD;
  constructor(public payload: { items: MetaAspect[] }) {}
}

export class RemoveAction implements Action {
  readonly type = ActionTypes.REMOVE;
  constructor(public payload: { ids: string[] }) {}
}

export type Actions = AddAction | RemoveAction;
