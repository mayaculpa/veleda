import { Action } from '@ngrx/store';
import { CanvasAspect } from '../../models';

export enum ActionTypes {
  ADD = '[CanvasAspect] Add',
  REMOVE = '[CanvasAspect] Remove'
}

export class AddAction implements Action {
  readonly type = ActionTypes.ADD;
  constructor(public payload: { items: CanvasAspect[] }) {}
}

export class RemoveAction implements Action {
  readonly type = ActionTypes.REMOVE;
  constructor(public payload: { ids: string[] }) {}
}

export type Actions = AddAction | RemoveAction;
