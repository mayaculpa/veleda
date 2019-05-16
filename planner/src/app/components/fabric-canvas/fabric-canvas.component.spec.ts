import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';

import { FabricCanvasComponent } from './fabric-canvas.component';
import { FabricService, toFabricObject } from '../../services/fabric.service';
import { createMockCanvasAspects } from '../../models';

let fabricServiceStub: Partial<FabricService>;

const aspects = createMockCanvasAspects();

fabricServiceStub = {
  objects: {
    [aspects[0].id]: toFabricObject(aspects[0]),
    [aspects[1].id]: toFabricObject(aspects[1])
  },
  addedFabricObjects$: new Subject<fabric.Object[]>(),
  changedFabricObjects$: new Subject<fabric.Object[]>(),
  removedFabricObjects$: new Subject<fabric.Object[]>()
};

describe('FabricCanvasComponent', () => {
  let component: FabricCanvasComponent;
  let fixture: ComponentFixture<FabricCanvasComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [FabricCanvasComponent],
      providers: [{ provide: FabricService, useValue: fabricServiceStub }]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FabricCanvasComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should add an object to the canvas', () => {
    const fabricObjects = createMockCanvasAspects().map(aspect => toFabricObject(aspect));
    fabricServiceStub.addedFabricObjects$.next(fabricObjects);

    // Check that fabric objects exist and have been added to the canvas
    expect(fabricObjects).toBeTruthy();
    fabricObjects.forEach(object => expect(component.canvas._objects.includes(object)).toBeTruthy());
  });
});
