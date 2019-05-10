import { Component, OnInit } from '@angular/core';
import {
  RootStoreState,
  CanvasAspectStoreSelectors,
  CanvasAspectStoreActions
} from '../../root-store';
import { select, Store } from '@ngrx/store';

import * as uuid from 'uuid';

@Component({
  selector: 'app-canvas-aspects',
  templateUrl: './canvas-aspects.component.html',
  styleUrls: ['./canvas-aspects.component.css']
})
export class CanvasAspectsComponent implements OnInit {
  canvasAspects$ = this.store$.pipe(select(CanvasAspectStoreSelectors.selectAllCanvasAspectItems));

  constructor(private store$: Store<RootStoreState.State>) {}

  ngOnInit() {}

  onAdd() {
    this.store$.dispatch(
      new CanvasAspectStoreActions.AddAction({
        items: [{ id: uuid.v4(), type: 'holla' }, { id: uuid.v4(), type: 'another' }]
      })
    );
  }
}
