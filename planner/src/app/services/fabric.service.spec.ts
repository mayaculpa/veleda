import { TestBed } from '@angular/core/testing';
import { StoreModule } from '@ngrx/store';

import { FabricService } from './fabric.service';
import { featureReducer } from '../root-store/canvas-aspect-store/reducer';

describe('FabricService', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot({}), StoreModule.forFeature('canvasAspect', featureReducer)]
    }).compileComponents()
  );

  it('should be created', () => {
    const service: FabricService = TestBed.get(FabricService);
    expect(service).toBeTruthy();
  });
});
