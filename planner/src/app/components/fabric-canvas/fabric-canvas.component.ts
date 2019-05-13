import {
  Component,
  OnInit,
  Input,
  ViewChild,
  ElementRef,
  AfterViewInit,
  OnDestroy
} from '@angular/core';
import { fabric } from 'fabric';
import { Observable, fromEvent, Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';

@Component({
  selector: 'app-fabric-canvas',
  templateUrl: './fabric-canvas.component.html',
  styleUrls: ['./fabric-canvas.component.css']
})
export class FabricCanvasComponent implements OnInit, AfterViewInit, OnDestroy {
  canvas: fabric.Canvas;

  // To be able to reference fabric objects by their ID, they are stored here
  objects: { [id: string]: fabric.Object } = {};

  @Input() addedFabricObject$: Observable<fabric.Object[]>;
  @Input() changedFabricObject$: Observable<fabric.Object[]>;
  @Input() removedFabricObject$: Observable<fabric.Object[]>;

  // Used to resize the canvas object
  @ViewChild('canvasContainer') canvasContainer: ElementRef;
  resizeObservable$: Observable<Event>;
  resizeSubscription$: Subscription;

  constructor() {}

  ngOnInit() {
    this.canvas = new fabric.Canvas('canvas');
    this.canvas.backgroundColor = 'gray';
    this.canvas.renderAll();

    this.resizeObservable$ = fromEvent(window, 'resize').pipe(debounceTime(300));
    this.resizeSubscription$ = this.resizeObservable$.subscribe(() => {
      this.canvas.setDimensions({
        width: this.canvasContainer.nativeElement.offsetWidth,
        height: this.canvasContainer.nativeElement.offsetHeight
      });
    });
  }

  ngAfterViewInit() {
    // Sets the canvas dimensions during the initial render
    this.canvas.setDimensions({
      width: this.canvasContainer.nativeElement.offsetWidth,
      height: this.canvasContainer.nativeElement.offsetHeight
    });
  }

  ngOnDestroy() {
    this.resizeSubscription$.unsubscribe();
  }
}
