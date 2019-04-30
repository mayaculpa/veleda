import { CanvasAspectStoreState } from './canvas-aspect-store';
import { MetaAspectStoreState } from './meta-aspect-store';

export interface State {
  canvasAspect: CanvasAspectStoreState.State;
  metaAspect: MetaAspectStoreState.State;
}
