import * as uuid from 'uuid';

export interface CanvasAspect {
  id: string;
  type: string;
}

export function createMockCanvasAspects(): CanvasAspect[] {
  return [{ id: uuid.v4(), type: 'Box' }, { id: uuid.v4(), type: 'Circle' }];
}
