import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { Store } from '@ngrx/store';
import { fabric } from 'fabric';

import { RootStoreState, CanvasAspectStoreSelectors } from '../root-store';
import { CanvasAspect } from '../models';

function toFabricObject(canvasAspect: CanvasAspect): fabric.Object {
  return new fabric.Rect({ name: canvasAspect.id,
    top: 50,
    left: 50,
    width: 80,
    height: 20,
    strokeWidth: 0,
    fill: 'blue'});
}

@Injectable({
  providedIn: 'root'
})
export class FabricCanvasAspectService {
  constructor(private store$: Store<RootStoreState.State>) {
    // Handle adding canvas aspects
    store$.select(CanvasAspectStoreSelectors.selectAddedCanvasAspects).subscribe(canvasAspects => {
      // Convert the canvas aspects to fabric objects so that they can be added to an HTML canvas
      const fabricObjects = canvasAspects.map(canvasAspect => toFabricObject(canvasAspect));
      this.addedFabricObjects$.next(fabricObjects);
      fabricObjects.forEach(fabricObject => (this.objects[fabricObject.name] = fabricObject));
    });

    // TODO: Handle updating canvas aspects

    // TODO: Handle removing canvas aspects
  }

  addedFabricObjects$ = new Subject<fabric.Object[]>();
  changedFabricObjects$ = new Subject<fabric.Object[]>();
  removedFabricObjects$ = new Subject<fabric.Object[]>();

  // To be able to reference fabric objects by their ID, they are stored here
  private objects: { [id: string]: fabric.Object } = {};

  getAllFabricObjects(): fabric.Object[] {
    return Object.values(this.objects);
  }
}
