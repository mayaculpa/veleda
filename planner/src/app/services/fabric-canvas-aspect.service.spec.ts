import { TestBed } from '@angular/core/testing';

import { FabricCanvasAspectService } from './fabric-canvas-aspect.service';

describe('FabricCanvasAspectService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: FabricCanvasAspectService = TestBed.get(FabricCanvasAspectService);
    expect(service).toBeTruthy();
  });
});
